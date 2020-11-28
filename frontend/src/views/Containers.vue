<template>
  <div class="containers">
    <top-bar title="Containers"></top-bar>
    <v-container>
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <v-data-iterator
            id="containers"
            :items="containers"
            :search="localState.search"
            :loading="loading">
            <template v-slot:header>
              <v-toolbar flat>
                <v-text-field id="search" v-model="localState.search" prepend-icon="mdi-magnify" label="Search..." single-line hide-details></v-text-field>
                <v-spacer></v-spacer>
                <v-dialog v-model="localState.showEdit" max-width="700px">
                  <template v-slot:activator="{ on, attrs }">
                    <v-btn v-if="collection && collection.canEdit(currentUser)" id="create-container" color="primary darken-1" text v-bind="attrs" v-on="on">Create Container</v-btn>
                  </template>
                  <v-card>
                    <v-card-title class="headline">{{editTitle}}</v-card-title>
                    <v-card-text>
                      <v-container>
                        <v-row>
                          <v-col cols="12">
                            <hsk-text-input 
                              id="name"
                              label="Name"
                              field="name"
                              :obj="localState.editItem"
                              :readonly="!!localState.editItem.id"
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
                        <v-row>
                          <v-col cols="12" md="4">
                            <hsk-text-input
                              label="Created"
                              :static-value="localState.editItem.createdAt | moment('YYYY-MM-DD HH:mm')"
                              ></hsk-text-input>
                          </v-col>
                          <v-col cols="12" md="4">
                            <hsk-text-input
                              label="Created By"
                              :static-value="localState.editItem.createdBy"></hsk-text-input>
                          </v-col>
                          <v-col cols="12" md="4">
                            <hsk-text-input
                              label="Updated"
                              :static-value="updatedAt"
                              ></hsk-text-input>
                          </v-col>
                        </v-row>
                      </v-container>
                    </v-card-text>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="secondary accent-1" text @click="closeEdit">Mabye not today.</v-btn>
                      <v-btn id="save" color="primary darken-1" text @click="save">Save It!</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-dialog v-model="localState.showDelete" max-width="500px">
                  <v-card>
                    <v-card-title class="headline">You really want to kill it?</v-card-title>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="secondary darken-1" text @click="closeDelete">Let mercy rule.</v-btn>
                      <v-btn color="warning darken-1" text @click="deleteContainerConfirm">Get it out of my sight.</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-btn id="refresh" color="primary darken-1" text @click="loadContainers()"><v-icon>mdi-refresh</v-icon></v-btn>
              </v-toolbar>
            </template>
            <template v-slot:default="props">
              <v-row>
                <v-col v-for="item in props.items" :key="item.id"
                    cols="12" md="6">
                  <v-card class="container">
                    <router-link class="text-decoration-none" :to="{ name: 'ContainerDetails', params: { entity: item.entityName, collection: item.collectionName, container: item.name } }">
                      <v-card-title class="text-h6">
                        <v-icon v-if="item.private">mdi-eye-off</v-icon>
                        <v-icon v-if="item.readOnly">mdi-lock</v-icon>
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
                      <v-list-item two-line>
                        <v-list-item-content>
                          <v-list-item-title>
                            {{item.description}}
                          </v-list-item-title>
                          <v-list-item-subtitle>
                            {{item.fullDescription}}
                          </v-list-item-subtitle>
                        </v-list-item-content>
                      </v-list-item>
                      <v-list-item two-line>
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
                          </v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                      <v-list-item two-lines>
                        <v-list-item-content>
                          <v-list-item-title>
                            {{item.createdAt | moment('YYYY-MM-DD HH:mm')}} | {{item.createdBy}}
                          </v-list-item-title>
                          <v-list-item-subtitle>
                            Created
                          </v-list-item-subtitle>
                        </v-list-item-content>
                      </v-list-item>
                    </v-list>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <template v-if="item.canEdit(currentUser)">
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
import moment from 'moment';
import { clone as _clone, find as _find } from 'lodash';

import { Container, Collection, User } from '../store/models';

interface State {
  search: string;
  editItem: Container;
  showEdit: boolean;
  showDelete: boolean;
}

function defaultItem(): Container {
  const item = new Container();
  item.createdAt = new Date();
  return item;
}


export default Vue.extend({
  name: 'Containers',
  mounted() {
    this.loadContainers();
  },
  data: (): { localState: State } => ({
    localState: {
      search: '',
      showEdit: false,
      showDelete: false,
      editItem: defaultItem(),
    },
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
    updatedAt(): string {
      return this.localState.editItem.updatedAt ?
        moment(this.localState.editItem.updatedAt).format('YYYY-MM-DD HH:mm') :
        '-';
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
      this.localState.showDelete = true;
    },
    deleteContainerConfirm() {
      this.$store.dispatch('containers/delete', this.localState.editItem)
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
        .then(upd => this.$store.commit('snackbar/showSuccess', 'Yay!'))
        .catch(err => this.$store.commit('snackbar/showError', err));
      this.closeEdit();
    },
    follow($event: MouseEvent) {
      $event.stopPropagation();
    },
  },
});

</script>