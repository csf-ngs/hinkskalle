<template>
  <div class="containers">
    <top-bar title="Containers"></top-bar>
    <v-container v-if="collection">
      <v-row cols="12" md="10" offset-md="1">
        <v-col>
          <h1 class="justify-center d-flex">
            <router-link class="text-decoration-none" :to="{ name: 'EntityCollections', params: { entity: collection.entityName } }">{{collection.entityName}}</router-link>/{{collection.name}}
          </h1>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <v-data-iterator
            id="containers"
            :items="containers"
            :search="localState.search"
            :sort-by="localState.sortBy"
            :sort-desc="localState.sortDesc"
            :loading="loading">
            <template v-slot:header>
              <v-toolbar flat>
                <v-text-field id="search" 
                  v-model="localState.search" 
                  prepend-inner-icon="mdi-magnify" 
                  label="Search..." 
                  single-line outlined dense
                  hide-details></v-text-field>
                <v-spacer></v-spacer>
                <v-select class="mr-1"
                  v-model="localState.sortBy" 
                  label="Sort..."
                  hide-details outlined dense
                  :items="sortKeys"
                  item-text="desc"
                  item-value="key"
                  prepend-inner-icon="mdi-sort"></v-select>
                <v-btn-toggle dense active-class="green--text" borderless
                  v-model="localState.sortDesc" mandatory>
                  <v-btn :value="true"><v-icon>mdi-sort-descending</v-icon></v-btn>
                  <v-btn :value="false"><v-icon>mdi-sort-ascending</v-icon></v-btn>
                </v-btn-toggle>
                <v-spacer></v-spacer>
                <v-dialog v-model="localState.showEdit" max-width="700px">
                  <template v-slot:activator="{ on, attrs }">
                    <v-btn 
                      v-if="collection && collection.canEdit" 
                      id="create-container" 
                      dense depressed
                      v-bind="attrs" v-on="on">Create Container</v-btn>
                  </template>
                  <v-card>
                    <v-card-title class="headline">{{editTitle}}</v-card-title>
                    <v-card-text>
                      <v-container>
                        <v-form v-model="localState.editValid">
                        <v-row>
                          <v-col cols="12">
                            <hsk-text-input 
                              id="name"
                              label="Name"
                              field="name"
                              :obj="localState.editItem"
                              :readonly="!!localState.editItem.id"
                              :check="[checkName]"
                              required
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="12">
                            <hsk-text-input 
                              id="description"
                              label="Description"
                              field="description"
                              :obj="localState.editItem"
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="12">
                            <hsk-text-input 
                              id="full-description"
                              label="Full Description"
                              field="fullDescription"
                              :obj="localState.editItem"
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="12">
                            <hsk-text-input 
                              id="vcs-url"
                              label="Git/VCS URL"
                              field="vcsUrl"
                              :obj="localState.editItem"
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="6">
                            <hsk-text-input 
                              type="yesno"
                              label="Private"
                              field="private"
                              :obj="localState.editItem"
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="6">
                            <hsk-text-input 
                              type="yesno"
                              label="Readonly"
                              field="readOnly"
                              :obj="localState.editItem"
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                        </v-row>
                        <v-row v-if="localState.editItem.id">
                          <v-col cols="12" md="4">
                            <hsk-user-input 
                              label="Owner"
                              :readonly="!currentUser.isAdmin"
                              v-model="localState.editItem.createdBy"
                              ></hsk-user-input>
                          </v-col>
                          <v-col cols="12" md="4">
                            <hsk-text-input
                              label="Created"
                              :static-value="localState.editItem.createdAt | prettyDateTime"
                              ></hsk-text-input>
                          </v-col>
                          <v-col cols="12" md="4">
                            <hsk-text-input
                              label="Updated"
                              :static-value="localState.editItem.updatedAt | prettyDateTime"
                              ></hsk-text-input>
                          </v-col>
                        </v-row>
                        </v-form>
                      </v-container>
                    </v-card-text>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="secondary accent-1" text @click="closeEdit">Mabye not today.</v-btn>
                      <v-btn id="save" color="primary darken-1" text :disabled="!localState.editValid" @click="save">Save It!</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-dialog v-model="localState.showDelete" max-width="600px">
                  <v-card>
                    <v-card-title class="headline">You really want to kill it?</v-card-title>
                    <v-card-text>
                      <v-checkbox v-model="localState.deleteCascade" label="Nuke Images & Tags"></v-checkbox>
                    </v-card-text>
                    <v-card-actions>
                      <v-btn color="secondary darken-1" text @click="closeDelete">Let mercy rule.</v-btn>
                      <v-spacer></v-spacer>
                      <v-btn color="warning darken-1" text @click="deleteContainerConfirm">Get it out of my sight.</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-spacer></v-spacer>
                <v-btn 
                  id="refresh" 
                  class="ml-2"
                  dense depressed 
                  @click="loadContainers()"><v-icon>mdi-refresh</v-icon></v-btn>
              </v-toolbar>
            </template>
            <template v-slot:default="props">
              <v-row>
                <v-col v-for="item in props.items" :key="item.id"
                    cols="12" md="6">
                  <v-card class="container">
                    <router-link class="text-decoration-none" :to="{ name: 'ContainerDetails', params: { entity: item.entityName, collection: item.collectionName, container: item.name } }">
                      <v-card-title class="text-h6">
                        <v-icon v-if="item.private">mdi-lock</v-icon>
                        <v-icon v-if="item.readOnly">mdi-pencil-off-outline</v-icon>
                        <span style="margin-right: 0.35rem;">
                          <container-type :container="item"></container-type>
                        </span>
                        {{item.name}}
                        <template v-if="item.vcsUrl">
                          <v-spacer></v-spacer>
                          <a :href="item.vcsUrl" @click="follow($event)" class="text-decoration-none">
                            <v-icon>mdi-source-repository</v-icon>
                          </a>
                        </template>
                      </v-card-title>
                    </router-link>
                    <v-divider></v-divider>
                    <v-list dense>
                      <v-list-item>
                        <v-list-item-content>
                          <v-list-item-title class="d-flex justify-space-between">
                            <div>
                              {{item.size}} {{item.size | pluralize('image')}}
                            </div>
                            <div>
                              <v-badge :content="item.downloadCount || '0'" inline color="blue-grey lighten-1">
                                <v-icon>mdi-download</v-icon>
                              </v-badge>
                              <container-stars :container="item"></container-stars>
                            </div>
                            <div>
                              {{item.usedQuota || 0 | prettyBytes()}}
                            </div>
                          </v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                      <v-list-item two-line>
                        <v-list-item-content>
                          <v-list-item-title>
                            {{item.description || '-'}}
                          </v-list-item-title>
                          <v-list-item-subtitle>
                            {{item.fullDescription || '-'}}
                          </v-list-item-subtitle>
                        </v-list-item-content>
                      </v-list-item>
                      <v-list-item two-lines>
                        <v-list-item-content>
                          <v-list-item-title class="d-flex justify-space-between">
                            <div>
                              {{item.createdAt | prettyDateTime}} | {{item.createdBy}}
                            </div>
                            <div>
                              {{item.updatedAt | prettyDateTime}} 
                            </div>
                          </v-list-item-title>
                          <v-list-item-subtitle class="d-flex justify-space-between">
                            <div>Created</div>
                            <div>Updated</div>
                          </v-list-item-subtitle>
                        </v-list-item-content>
                      </v-list-item>
                    </v-list>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <template v-if="item.canEdit">
                        <v-icon small class="mr-1" @click="editContainer(item)">mdi-pencil</v-icon>
                        <v-icon small @click="deleteContainer(item)">mdi-delete</v-icon>
                      </template>
                      <template v-else>
                        <v-icon small>mdi-cancel</v-icon>
                      </template>
                    </v-card-actions>
                  </v-card>
                </v-col>
              </v-row>
            </template>
          </v-data-iterator>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>
<script lang="ts">
import Vue from 'vue';
import { clone as _clone, } from 'lodash';

import { Container, Collection, User, checkName } from '../store/models';
import UserInput from '@/components/UserInput.vue';
import ContainerType from '@/components/ContainerType.vue';

interface State {
  search: string;
  sortBy: string;
  sortDesc: boolean;
  editItem: Container;
  editValid: boolean;
  showEdit: boolean;
  showDelete: boolean;
  deleteCascade: boolean;
}

function defaultItem(): Container {
  const item = new Container();
  item.createdAt = new Date();
  return item;
}


export default Vue.extend({
  name: 'HskContainers',
  components: { 'hsk-user-input': UserInput, ContainerType },
  mounted() {
    this.loadContainers();
  },
  data: (): { localState: State; sortKeys: {key: string; desc: string}[] } => ({
    localState: {
      search: '',
      sortBy: 'name',
      sortDesc: false,
      showEdit: false,
      showDelete: false,
      deleteCascade: false,
      editItem: defaultItem(),
      editValid: true,
    },
    sortKeys: [
      { key: 'name', desc: 'Name' }, 
      { key :'createdAt', desc: "Create Date" }, 
      { key: 'updatedAt', desc: "Last Updated" },
      { key: 'downloadCount', desc: "Downloads" },
      { key: 'stars', desc: "Stars" },
      { key: 'size', desc: '# Images' } ,
      { key: 'usedQuota', desc: 'Size' },
    ],
  }),
  computed: {
    containers(): Container[] {
      return this.$store.getters['containers/list'];
    },
    collection(): Collection {
      return this.$store.getters['containers/currentCollection'];
    },
    loading(): boolean {
      return this.$store.getters['containers/status']==='loading';
    },
    editTitle(): string {
      return this.localState.editItem.id ? 'Edit Container' : 'New Container';
    },
    currentUser(): User {
      return this.$store.getters.currentUser;
    },
  },
  watch: {
    $route() {
      this.loadContainers();
    },
    'localState.showEdit': function showEdit(val) {
      if (!val) {
        this.closeEdit();
      }
    },
    'localState.showDelete': function showDelete(val) {
      if (!val) {
        this.closeDelete();
      }
    },
  },
  methods: {
    loadContainers() {
      this.$store.dispatch('containers/list', { entityName: this.$route.params.entity, collectionName: this.$route.params.collection })
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    editContainer(container: Container) {
      this.localState.editItem = _clone(container);
      this.localState.showEdit = true;
    },
    deleteContainer(container: Container) {
      this.localState.editItem = _clone(container);
      this.localState.deleteCascade = false;
      this.localState.showDelete = true;
    },
    deleteContainerConfirm() {
      this.$store.dispatch('containers/delete', { container: this.localState.editItem, cascade: this.localState.deleteCascade })
        .then(() => this.$store.commit('snackbar/showSuccess', "It's gone!"))
        .catch(err => this.$store.commit('snackbar/showError', err));
      this.closeDelete();
    },
    closeEdit() {
      this.localState.showEdit = false;
      this.$nextTick(() => {
        this.localState.editItem = defaultItem();
      });
    },
    closeDelete() {
      this.localState.showDelete = false;
      this.$nextTick(() => {
        this.localState.editItem = defaultItem();
      });
    },
    save() {
      const action = this.localState.editItem.id ?
        'containers/update' : 'containers/create';
      this.localState.editItem.entityName = this.$route.params.entity;
      this.localState.editItem.collectionName = this.$route.params.collection;

      this.$store.dispatch(action, this.localState.editItem)
        .then(() => this.$store.commit('snackbar/showSuccess', 'Yay!'))
        .catch(err => this.$store.commit('snackbar/showError', err));
      this.closeEdit();
    },
    follow($event: MouseEvent) {
      $event.stopPropagation();
    },
    checkName(name: string): string | boolean {
      return checkName(name);
    },
  },
});

</script>