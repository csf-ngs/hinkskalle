<template>
  <div class="collections">
    <top-bar title="Collections"></top-bar>
    <v-container v-if="entity">
      <v-row cols="12" md="10" offset-md="1">
        <v-col>
          <h1 class="justify-center d-flex">
            {{entity.name}}
          </h1>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <v-data-iterator
            id="collections"
            :items="collections"
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
                  single-line outlined dense hide-details></v-text-field>
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
                      v-if="entity && entity.canEdit(currentUser)" 
                      id="create-collection" 
                      dense depressed
                      v-bind="attrs" v-on="on">Create Collection</v-btn>
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
                              required
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="12">
                            <hsk-text-input 
                              type="yesno"
                              label="Private"
                              field="private"
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
                              :static-value="localState.editItem.createdAt | moment('YYYY-MM-DD HH:mm')"
                              ></hsk-text-input>
                          </v-col>
                          <v-col cols="12" md="4">
                            <hsk-text-input
                              label="Updated"
                              :static-value="updatedAt"
                              ></hsk-text-input>
                          </v-col>
                        </v-row>
                        </v-form>
                      </v-container>
                    </v-card-text>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="secondary accent-1" text @click="closeEdit">Mabye not today.</v-btn>
                      <v-btn id="save" color="primary darken-1" :disabled="!localState.editValid" text @click="save">Save It!</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-dialog v-model="localState.showDelete" max-width="500px">
                  <v-card>
                    <v-card-title class="headline">You really want to kill it?</v-card-title>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="secondary darken-1" text @click="closeDelete">Let mercy rule.</v-btn>
                      <v-btn color="warning accent-1" text @click="deleteCollectionConfirm">Get it out of my sight.</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-spacer></v-spacer>
                <v-btn 
                  id="refresh" 
                  class="ml-2"
                  dense depressed 
                  @click="loadCollections()"><v-icon>mdi-refresh</v-icon></v-btn>
              </v-toolbar>
            </template>
            <template v-slot:default="props">
              <v-row>
                <v-col v-for="item in props.items" :key="item.id"
                  cols="12" md="6">
                  <v-card class="collection">
                    <router-link :to="{ name: 'Containers', params: { entity: item.entityName, collection: item.name } }" class="text-decoration-none">
                      <v-card-title class="headline">
                        <v-icon v-if="item.private">mdi-eye-off</v-icon>
                        {{item.name}}
                      </v-card-title>
                    </router-link>
                    <v-divider></v-divider>
                    <v-list dense>
                      <v-list-item>
                        <v-list-item-content>
                          <v-list-item-title class="d-flex justify-space-between">
                            <div>
                              {{item.size}} {{item.size | pluralize('container')}}
                            </div>
                            <div>
                              {{item.usedQuota || 0 | prettyBytes()}}
                            </div>
                          </v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-content>
                          <v-list-item-title>
                            {{item.description || '-'}}
                          </v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                      <v-list-item two-lines>
                        <v-list-item-content>
                          <v-list-item-title class="d-flex justify-space-between">
                            <div>
                              {{item.createdAt | moment('YYYY-MM-DD HH:mm')}} | {{item.createdBy}}
                            </div>
                            <div>
                              {{item.updatedAt | moment('YYYY-MM-DD HH:mm')}} 
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
                      <template v-if="item.canEdit(currentUser)">
                        <v-icon small class="mr-1" @click="editCollection(item)">mdi-pencil</v-icon>
                        <v-icon small @click="deleteCollection(item)">mdi-delete</v-icon>
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
import { Collection, Entity, User, checkName } from '../store/models';
import Vue from 'vue';
import { DataTableHeader } from 'vuetify';

import { clone as _clone } from 'lodash';
import moment from 'moment';
import UserInput from '@/components/UserInput.vue';

interface State {
  search: string;
  sortBy: string;
  sortDesc: boolean;
  editItem: Collection;
  editValid: boolean;
  showEdit: boolean;
  showDelete: boolean;
}

function defaultItem(): Collection {
  const item = new Collection();
  item.createdAt = new Date();
  return item;
}

export default Vue.extend({
  name: 'Collections',
  components: { 'hsk-user-input': UserInput },
  mounted() {
    this.loadCollections();
  },
  data: (): { localState: State; sortKeys: { key: string; desc: string }[] } => ({
    localState: {
      search: '',
      sortBy: 'name',
      sortDesc: false,
      showEdit: false,
      showDelete: false,
      editItem: defaultItem(),
      editValid: true,
    },
    sortKeys: [
      { key: 'name', desc: 'Name' }, 
      { key :'createdAt', desc: "Create Date" }, 
      { key: 'updatedAt', desc: "Last Updated" },
      { key: 'size', desc: '# Containers' },
      { key: 'usedQuota', desc: 'Size' },
    ],
  }),
  computed: {
    collections(): Collection[] {
      return this.$store.getters['collections/list'];
    },
    loading(): boolean {
      return this.$store.getters['collections/status']==='loading';
    },
    editTitle(): string {
      return this.localState.editItem.id ? 'Edit Collection' : 'New Collection';
    },
    updatedAt(): string {
      return this.localState.editItem.updatedAt ?
        moment(this.localState.editItem.updatedAt).format('YYYY-MM-DD HH:mm') :
        '-';
    },
    entity(): Entity {
      return this.$store.getters['collections/currentEntity'];
    },
    currentUser(): User {
      return this.$store.getters.currentUser;
    }
  },
  watch: {
    $route() {
      this.loadCollections();
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
    loadCollections() {
      this.$store.dispatch('collections/list', this.$route.params.entity)
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    editCollection(collection: Collection) {
      this.localState.editItem = _clone(collection);
      this.localState.showEdit = true;
    },
    deleteCollection(collection: Collection) {
      this.localState.editItem = _clone(collection);
      this.localState.showDelete = true;
    },
    deleteCollectionConfirm() {
      this.$store.dispatch('collections/delete', this.localState.editItem)
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
        'collections/update' : 'collections/create';
      if (this.$route.params.entity) {
        this.localState.editItem.entityName = this.$route.params.entity;
      }
      this.$store.dispatch(action, this.localState.editItem)
        .then(upd => this.$store.commit('snackbar/showSuccess', 'Yay!'))
        .catch(err => this.$store.commit('snackbar/showError', err));
      this.closeEdit();
    },
    checkName(name: string): string | boolean {
      return checkName(name);
    },
  }
});
</script>